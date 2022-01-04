from app import socket, app
import app.views

        
if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    socket.run(app, debug=True)
    






