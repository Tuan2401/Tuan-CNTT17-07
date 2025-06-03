Mục tiêu:Xây dựng một ứng dụng chat thời gian thực qua trình duyệt có:
            
            Giao diện web đơn giản, dễ dùng

            Đăng nhập bằng tên người dùng

            Tạo/Tham gia phòng chat

            Gửi tin nhắn công khai (gửi nhóm) hoặc riêng tư (gửi cá nhân)

            Mã hóa tin nhắn bằng AES (CBC mode) để đảm bảo bảo mật nội dung


Công nghệ/Kỹ thuật	                                                 Vai trò

    HTML, Bootstrap, JavaScript, Socket.IO, CryptoJS          	Giao diện chat, gửi/nhận và giải mã tin nhắn
	
    Flask + Flask-SocketIO	                                    Quản lý phòng, người dùng, chuyển tiếp tin nhắn

    AES	Crypto.Cipher.AES (server) + CryptoJS.AES (client JS)	  Mã hóa/decrypt tin nhắn
	
    session['username']	                                        Quản lý người dùng đang đăng nhập
	
    Socket.IO	                                                  Giao tiếp thời gian thực giữa client-server


Chức năng	                                                          Mô tả

    Đăng nhập	                                                  Nhập username (không mật khẩu)
    Tạo phòng	                                                  Nhập tên phòng và tạo mới
    Vào phòng	                                                  Nhấp tên phòng để vào
    Gửi nhóm	                                                  Gửi tin nhắn đến toàn bộ thành viên phòng
    Gửi riêng	                                                  Gửi tin nhắn đến người cụ thể trong phòng
    Mã hóa	                                                    Tin nhắn được mã hóa bằng AES (CBC), chỉ giải mã được nếu người nhận biết key
    Nhận biết người dùng và phòng                              	Quản lý users_online, user_rooms, rooms bằng socketio
    Hệ thống thông báo	                                        "XYZ đã vào phòng", "XYZ đã rời phòng", v.v.

![image](https://github.com/user-attachments/assets/c03f4178-f92b-4683-ab42-a759fc9b6795)

![image](https://github.com/user-attachments/assets/f342af1d-f971-4129-94fc-7242fe1b07e7)
