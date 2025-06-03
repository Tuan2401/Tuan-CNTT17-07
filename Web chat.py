from flask import Flask, render_template_string, request, redirect, session, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64

app = Flask(__name__)
app.secret_key = 'your-secret-key'
socketio = SocketIO(app)
users_online = {}   # sid -> username
user_rooms = {}     # sid -> room
rooms = {}          # room_name -> list of usernames

def encrypt_message(key, message):
    key = pad(key.encode(), 16)[:16]
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(message.encode(), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return iv + ":" + ct

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        if username:
            session['username'] = username
            return redirect(url_for('chat'))
    return '''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
      <meta charset="UTF-8">
      <title>Đăng nhập</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
    <div class="d-flex justify-content-center align-items-center" style="height:100vh;">
      <form method="POST" class="card p-4 shadow" style="min-width:300px;">
        <h4 class="text-center mb-3">Đăng nhập</h4>
        <input type="text" name="username" class="form-control mb-2" placeholder="Tên người dùng" required>
        <button type="submit" class="btn btn-primary w-100">Vào phòng chat</button>
      </form>
    </div>
    </body>
    </html>
    '''

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
      <meta charset="UTF-8">
      <title>Phòng Chat</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
      <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js"></script>
      <style>
        #chat-box {{ height: 300px; overflow-y: auto; background: #fff; padding:10px; border-radius:8px; border:1px solid #ccc }}
      </style>
    </head>
    <body>
    <div class="container mt-4">
      <h3 class="text-center">🔐 Xin chào {username}!</h3>
      <div class="row">
        <div class="col-md-3">
          <h5>Phòng chat</h5>
          <input id="new-room" class="form-control mb-2" placeholder="Tạo phòng mới">
          <button class="btn btn-success mb-3 w-100" onclick="createRoom()">Tạo phòng</button>
          <h6>Phòng hiện có</h6>
          <ul id="room-list" class="list-group mb-3" style="max-height:200px; overflow-y:auto;"></ul>

          <h5>👥 Thành viên phòng</h5>
          <ul id="user-list" class="list-group"></ul>
        </div>
        <div class="col-md-9">
          <h5>Phòng: <span id="current-room">Chưa chọn</span></h5>
          <input type="text" id="aes-key" class="form-control mb-2" placeholder="Nhập khóa AES">
          <div id="chat-box"></div>
          <div class="input-group mt-2">
            <input type="text" id="message" class="form-control" placeholder="Tin nhắn...">
            <select id="recipient" class="form-select" style="max-width:150px">
              <option value="all">Gửi nhóm</option>
            </select>
            <button class="btn btn-primary" onclick="sendMessage()">Gửi</button>
          </div>
        </div>
      </div>
    </div>

    <script>
      const username = "{username}";
      // Kết nối socket IO: kết nối với cùng host, port nơi chạy server
      const socket = io(location.origin);

      let currentRoom = null;

      socket.emit('user_connected', username);

      socket.on('room_list', (rooms) => {{
        const list = document.getElementById('room-list');
        list.innerHTML = '';
        rooms.forEach(room => {{
          const li = document.createElement('li');
          li.className = 'list-group-item list-group-item-action';
          li.textContent = room;
          li.style.cursor = 'pointer';
          li.onclick = () => joinRoom(room);
          list.appendChild(li);
        }});
      }});

      socket.on('update_room_users', (users) => {{
        const userList = document.getElementById('user-list');
        const select = document.getElementById('recipient');
        userList.innerHTML = '';
        select.innerHTML = '<option value="all">Gửi nhóm</option>';
        users.forEach(user => {{
          userList.innerHTML += `<li class="list-group-item">${{user}}</li>`;
          if(user !== username) {{
            select.innerHTML += `<option value="${{user}}">${{user}}</option>`;
          }}
        }});
      }});

      socket.on('receive_message', (data) => {{
        const key = document.getElementById('aes-key').value;
        const box = document.getElementById('chat-box');
        const decrypted = decryptMessage(data.encrypted, key);
        const div = document.createElement('div');
        div.innerHTML = `<strong>${{data.from}} đến ${{data.to}}:</strong> ${{decrypted}} <br><small class="text-muted">[Đã mã hóa]</small><hr>`;
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
      }});

      function decryptMessage(encrypted, key) {{
        try {{
          const [iv_b64, ct_b64] = encrypted.split(":");
          const iv = CryptoJS.enc.Base64.parse(iv_b64);
          const ct = CryptoJS.enc.Base64.parse(ct_b64);
          const decrypted = CryptoJS.AES.decrypt({{
            ciphertext: ct
          }}, CryptoJS.enc.Utf8.parse(key.padEnd(16, '\\0').substring(0,16)), {{
            iv: iv,
            padding: CryptoJS.pad.Pkcs7,
            mode: CryptoJS.mode.CBC
          }});
          return decrypted.toString(CryptoJS.enc.Utf8);
        }} catch {{
          return "(Không giải mã được)";
        }}
      }}

      function sendMessage() {{
        const msg = document.getElementById('message').value;
        const key = document.getElementById('aes-key').value;
        const to = document.getElementById('recipient').value;
        if (!msg || !key) {{
          alert("Nhập cả tin nhắn và khóa AES!");
          return;
        }}
        if (!currentRoom) {{
          alert("Bạn phải chọn phòng trước!");
          return;
        }}
        socket.emit('send_message', {{
          from: username,
          to: to,
          key: key,
          message: msg,
          room: currentRoom
        }});
        document.getElementById('message').value = "";
      }}

      function createRoom() {{
        const newRoom = document.getElementById('new-room').value.trim();
        if(newRoom) {{
          socket.emit('create_room', newRoom);
          document.getElementById('new-room').value = '';
        }}
      }}

      function joinRoom(room) {{
        if(currentRoom) {{
          socket.emit('leave_room', currentRoom);
        }}
        socket.emit('join_room', room);
        currentRoom = room;
        document.getElementById('current-room').textContent = room;
        document.getElementById('chat-box').innerHTML = '';
      }}

    </script>
    </body>
    </html>
    ''')

@socketio.on('user_connected')
def handle_user(username):
    users_online[request.sid] = username
    # Gửi danh sách phòng hiện có cho user mới kết nối
    emit('room_list', list(rooms.keys()), room=request.sid)

@socketio.on('create_room')
def handle_create_room(room):
    if room not in rooms:
        rooms[room] = []
    # Cập nhật danh sách phòng cho tất cả user
    emit('room_list', list(rooms.keys()), broadcast=True)

@socketio.on('join_room')
def handle_join_room(room):
    username = users_online.get(request.sid)
    if not username:
        return
    # Nếu user đang trong phòng khác, rời trước
    old_room = user_rooms.get(request.sid)
    if old_room:
        leave_room(old_room)
        if username in rooms.get(old_room, []):
            rooms[old_room].remove(username)
        emit('update_room_users', rooms[old_room], room=old_room)
        emit('receive_message', {
            'from': 'Hệ thống',
            'to': old_room,
            'encrypted': encrypt_message('key', f'{username} đã rời phòng {old_room}')
        }, room=old_room)

    join_room(room)
    user_rooms[request.sid] = room
    if room not in rooms:
        rooms[room] = []
    if username not in rooms[room]:
        rooms[room].append(username)

    emit('update_room_users', rooms[room], room=room)
    emit('receive_message', {
        'from': 'Hệ thống',
        'to': room,
        'encrypted': encrypt_message('key', f'{username} đã vào phòng {room}')
    }, room=room)

@socketio.on('leave_room')
def handle_leave_room(room):
    username = users_online.get(request.sid)
    if not username:
        return
    leave_room(room)
    if username in rooms.get(room, []):
        rooms[room].remove(username)
    user_rooms.pop(request.sid, None)
    emit('update_room_users', rooms[room], room=room)
    emit('receive_message', {
        'from': 'Hệ thống',
        'to': room,
        'encrypted': encrypt_message('key', f'{username} đã rời phòng {room}')
    }, room=room)

@socketio.on('send_message')
def handle_message(data):
    from_user = data['from']
    to_user = data['to']
    key = data['key']
    message = data['message']
    room = data.get('room')
    encrypted = encrypt_message(key, message)
    msg_data = {
        'from': from_user,
        'to': 'nhóm' if to_user == 'all' else to_user,
        'encrypted': encrypted
    }
    if room:
        if to_user == 'all':
            emit('receive_message', msg_data, room=room)
        else:
            # Gửi riêng cho to_user và from_user trong phòng
            for sid, user in users_online.items():
                if user == to_user or user == from_user:
                    if user_rooms.get(sid) == room:
                        emit('receive_message', msg_data, room=sid)

@socketio.on('disconnect')
def handle_disconnect():
    username = users_online.pop(request.sid, None)
    room = user_rooms.pop(request.sid, None)
    if room and username and room in rooms and username in rooms[room]:
        rooms[room].remove(username)
        emit('update_room_users', rooms[room], room=room)
        emit('receive_message', {
            'from': 'Hệ thống',
            'to': room,
            'encrypted': encrypt_message('key', f'{username} đã ngắt kết nối')
        }, room=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
