"""
 HTTP Server Shell
 Author: Ofri Guz
 Date: December 30, 2023,
 Purpose: Ex. 4
"""
# Modules
import socket
import os
import logging
import urllib.parse
from urllib.parse import urlparse


ROOT_URL = "C:\\work\\cyber\\"
# Constants
DEFAULT_URL = "/index.html"
ROOT_WEB = ROOT_URL + "webroot"
ERROR_IMAGE_NAME = "404.jpg"
ERROR_PATH = r"special_images/" + ERROR_IMAGE_NAME
UPLOAD_DIR = ROOT_WEB + "\\uploads"

OK = 200
FOUND = 302
INVALID_REQUEST_ERROR = 400
FILE_NOT_FOUND_ERROR = 404
FORBIDDEN_ERROR = 403
INTERNAL_SERVER_ERROR = 500
PICTURE_NOT_FOUND_ERROR = 501

HTTP_DICTIONARY = {
    OK: 'HTTP/1.1 200 OK\r\n',
    FOUND: 'HTTP/1.1 302 Found\r\n',
    INVALID_REQUEST_ERROR: 'HTTP/1.1 ' + str(INVALID_REQUEST_ERROR) + ' Bad Request\r\n',  # **********
    FORBIDDEN_ERROR: 'HTTP/1.1 ' + str(FORBIDDEN_ERROR) + ' Forbidden\r\n',  # **************
    FILE_NOT_FOUND_ERROR: 'HTTP/1.1 ' + str(FILE_NOT_FOUND_ERROR) + ' Not Found\r\n',  # **************
    INTERNAL_SERVER_ERROR: 'HTTP/1.1 ' + str(INTERNAL_SERVER_ERROR) + ' Internal Server Error\r\n',
    PICTURE_NOT_FOUND_ERROR: 'HTTP/1.1 ' + str(PICTURE_NOT_FOUND_ERROR) + ' PictureNotFound\r\n'
}

REDIRECTION_DICTIONARY = {
    '/forbidden': (FORBIDDEN_ERROR, "Forbidden"),
    '/moved': (HTTP_DICTIONARY[FOUND], '/index.html'),
    '/error': (INTERNAL_SERVER_ERROR, "Internal Server Error"),
}

QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 2
BUFFER_SIZE = 1024


def protocol_receive(my_socket):
    """
    Protocol to receive message from client to server
    :param my_socket: The socket for communication
    :return: message sent from client
    """
    headers = ''
    try:
        while not headers.endswith('\r\n\r\n'):
            chunk = my_socket.recv(1).decode()
            if not chunk:
                # if client sends empty msg
                break
            headers += chunk
            # message += my_socket.recv(1).decode()
        return headers

    except socket.error as e:
        logging.error(f"Socket error: {e}")
        return ''
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return ''


def get_file_data(file_name):
    """
    Get data from file
    :param file_name: the name of the file
    :return: the file data in a string
    """
    try:
        with open(file_name, 'rb') as file:
            return file.read()
    except FileNotFoundError:
        logging.error(f"Error: File '{file_name}' not found.")
    except OSError as e:
        logging.error(f"An unexpected error occurred: {e}")


def get_content_type(file_type):
    """
    Get the Content-Type header based on the file type
    :param file_type: The file type
    :return: The content type
    """
    content_types = {
        'html': 'text/html;charset=utf-8',
        'jpg': 'image/jpeg',
        'css': 'text/css',
        'js': 'text/javascript; charset=UTF-8',
        'txt': 'text/plain',
        'ico': 'image/x-icon',
        'gif': 'image/jpeg',
        'png': 'image/png',
    }
    return content_types.get(file_type, 'application/octet-stream')


def handle_error(client_socket, status_code, status_text):
    """
    Send an error response to the client
    :param client_socket: The client socket
    :param status_code: The status code
    :param status_text: The status text
    :return:
    """
    if status_code == FILE_NOT_FOUND_ERROR:
        # Custom Not Found Page with Image
        error_page_path = ERROR_PATH
        image_path = ERROR_PATH
        if os.path.exists(error_page_path):
            with open(error_page_path, 'rb') as error_page_file:
                error_page_data = error_page_file.read()
            content_type = 'text/html;charset=utf-8'
        else:
            error_page_data = b"<html><body><h1>404 Not Found</h1></body></html>"
            content_type = 'text/html;charset=utf-8'
        if os.path.exists(image_path):
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            image_content_type = 'image/jpeg'
            content_type += f"\r\nContent-Type: {image_content_type}"
            # Add image data to the error page
            error_page_data = error_page_data.replace(b"<!-- INSERT_IMAGE_HERE -->", image_data)
        error_header = f"{HTTP_DICTIONARY[status_code]}Content-Type: {content_type}\r\nContent-Length: {len(error_page_data)}\r\n\r\n"
        error_response = error_header.encode() + error_page_data
        client_socket.send(error_response)
    else:
        error_message = f"{status_code} {status_text}"
        if status_code in HTTP_DICTIONARY:
            http_beginner = HTTP_DICTIONARY[status_code]
        error_header = (
            f"{http_beginner}Content-Type: text/plain\r\nContent-Length: {len(error_message)}\r\n\r\n"
        )
        error_response = error_header.encode() + error_message.encode()
        client_socket.send(error_response)


def handle_redirection(client_socket, new_location):
    """
    Send a redirection response to the client
    :param client_socket: The client socket
    :param new_location: The new location
    :return: None
    """
    redirection_header = f"{HTTP_DICTIONARY[FOUND]}Location: {new_location}\r\n\r\n"
    redirection_response = redirection_header.encode()
    client_socket.send(redirection_response)


def calculate_next(query_params, client_socket):
    """
    Return next number
    :param query_params: Current number
    :param client_socket:
    :return: Next Number
    """
    if 'num' in query_params:
        try:
            num = int(query_params['num'][0])
            next_num = num + 1
            response_body = str(next_num)
            content_length = len(response_body)
            http_header = f"{HTTP_DICTIONARY[OK]}Content-Type: text/plain;charset=utf-8\r\nContent-Length: {content_length}\r\n\r\n"
            http_response = http_header.encode() + response_body.encode()
            client_socket.send(http_response)
            return
        except ValueError:
            handle_error(client_socket, INVALID_REQUEST_ERROR, "Bad Request")
            return
    else:
        handle_error(client_socket, INVALID_REQUEST_ERROR, "Bad Request")
        return


def calculate_area(query_params, client_socket):
    """
    Calculate area of triangle
    :param query_params:  height and width
    :param client_socket:
    :return: area of triangle
    """
    if 'height' in query_params and 'width' in query_params:
        try:
            height = int(query_params['height'][0])
            width = int(query_params['width'][0])
            area = (height * width)/2
            response_body = str(area)
            content_length = len(response_body)
            http_header = f"{HTTP_DICTIONARY[OK]}Content-Type: text/plain;charset=utf-8\r\nContent-Length: {content_length}\r\n\r\n"
            http_response = http_header.encode() + response_body.encode()
            client_socket.send(http_response)
            return
        except ValueError:
            handle_error(client_socket, INVALID_REQUEST_ERROR, "Bad Request")
            return
    else:
        handle_error(client_socket, INVALID_REQUEST_ERROR, "Bad Request")
        return


def handle_upload(query_params, client_socket, headers):
    """
    Handle Upload Function
    :param query_params: File path
    :param client_socket:
    :param headers: message request - for content length
    :return:
    """
    if 'file-name' in query_params:
        try:
            file_name = query_params['file-name'][0]
            upload_path = os.path.join(UPLOAD_DIR, file_name)

            if os.path.exists(upload_path):
                handle_error(client_socket, INVALID_REQUEST_ERROR, "File already exists")
                return

            # Read the file data from the request body
            content_length_str = headers.split('Content-Length: ')[1].split('\r\n')[0]
            content_length = int(content_length_str) if content_length_str.isdigit() else 0

            # Read the request body based on the Content-Length
            chunk_size = 1
            if content_length >= 1000000:
                SOCKET_TIMEOUT = 5
                chunk_size = 1000
                client_socket.settimeout(SOCKET_TIMEOUT)
            message = b''
            while len(message) < content_length:
                chunk = client_socket.recv(chunk_size)
                if not chunk:
                    # if client sends empty msg
                    break
                message += chunk

            # Save the file to the upload directory
            with open(upload_path, 'wb') as file:
                file.write(message)

            # Send a response to the client
            response_body = "OK"
            response_header = (
                f"{HTTP_DICTIONARY[OK]}Content-Type: text/plain;charset=utf-8\r\n"
                f"Content-Length: {len(response_body)}\r\n\r\n"
            )
            response = response_header.encode() + response_body.encode()
            client_socket.send(response)
            SOCKET_TIMEOUT = 2
            client_socket.settimeout(SOCKET_TIMEOUT)

        except Exception as e:
            handle_error(client_socket, INTERNAL_SERVER_ERROR, "Internal Server Error")
            logging.error(f"An unexpected error occurred during file upload: {e}")
    else:
        handle_error(client_socket, INVALID_REQUEST_ERROR, "Bad Request")


def handle_image(query_params, client_socket):
    if 'image-name' in query_params:
        try:
            image_name = query_params['image-name'][0]
            image_path = os.path.join(UPLOAD_DIR, image_name)

            if os.path.exists(image_path):
                # Read the data from the image file
                image_data = get_file_data(image_path)

                # Extract file extension from the image name
                _, image_extension = os.path.splitext(image_name)

                # Build HTTP response header
                http_header = f"{HTTP_DICTIONARY[OK]}Content-Type: image/{image_extension[1:]}\r\n"
                http_header += f"Content-Length: {len(image_data)}\r\n\r\n"

                # Send the HTTP header and image data to the client
                http_response = http_header.encode() + image_data
                client_socket.send(http_response)
            else:
                # Image not found, send 404 response
                handle_error(client_socket, PICTURE_NOT_FOUND_ERROR, "Not Found")
        except Exception as e:
            handle_error(client_socket, INTERNAL_SERVER_ERROR, "Internal Server Error")
            logging.error(f"An unexpected error occurred during image handling: {e}")
    else:
        # Invalid request, send 400 response
        handle_error(client_socket, INVALID_REQUEST_ERROR, "Bad Request")


def validate_http_request(request):
    """
    Check if request is a valid HTTP request and returns TRUE / FALSE and
    the requested URL
    :param request: the request which was received from the client
    :return: a tuple of (True/False - depending on if the request is valid,
    the requested resource )
    """
    try:
        request_line = request.split('\r\n')
        message_split = request_line[0].split(' ')
        if len(message_split) != 3:
            return False, ''
        method, resource, http_version = message_split
        if method not in ['GET', 'POST'] or http_version != "HTTP/1.1":
            return False, ''
        return True, resource
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return False, ''


def handle_client_request(resource, client_socket, client_request):
    """
    Check the required resource, generate proper HTTP response and send
    to client
    :param resource: the required resource
    :param client_socket: a socket for the communication with the client
    :param client_request: what the client requested
    :return: None
    """
    if resource == '/' or resource == ' ':
        uri = DEFAULT_URL
    else:
        uri = resource

    parsed_url = urlparse(uri)
    path_without_query = parsed_url.path

    filename = ROOT_WEB + path_without_query
    # filename = ROOT_WEB + uri
    if '/calculate-next' in uri:
        query_params = urllib.parse.parse_qs(uri.split('?')[1])
        calculate_next(query_params, client_socket)
    if '/calculate-area' in uri:
        query_params = urllib.parse.parse_qs(uri.split('?')[1])
        calculate_area(query_params, client_socket)
    if '/upload' in uri:
        query_params = urllib.parse.parse_qs(parsed_url.query)
        handle_upload(query_params, client_socket, client_request)
        return
    if '/image' in uri:
        query_params = urllib.parse.parse_qs(parsed_url.query)
        handle_image(query_params, client_socket)
        return

    if uri in REDIRECTION_DICTIONARY:
        status_code, response_data = REDIRECTION_DICTIONARY[uri]
        if status_code == HTTP_DICTIONARY[FOUND]:
            handle_redirection(client_socket, response_data)
        else:
            handle_error(client_socket, status_code, response_data)
        return

    if not os.path.exists(filename) or not os.path.isfile(filename):
        handle_error(client_socket, FILE_NOT_FOUND_ERROR, "Not Found")
        return

    file_type = uri.split('.')[-1]
    http_header = f"{HTTP_DICTIONARY[OK]}Content-Type: {get_content_type(file_type)}\r\n"

    # Read the data from the file
    data = get_file_data(filename)
    if data is None:
        return
    http_header += f"Content-Length: {len(data)}\r\n\r\n"

    # http_header should be encoded before sent
    # data encoding depends on its content. text should be encoded, while files shouldn't
    http_response = http_header.encode() + data
    client_socket.send(http_response)


def handle_client(client_socket):
    """
    Handles client requests: verifies client's requests are legal HTTP, calls
    function to handle the requests
    :param client_socket: the socket for the communication with the client
    :return: None
    """
    logging.info("Client connected")
    try:
        while True:
            logging.debug("in handle client loop")
            client_request = protocol_receive(client_socket)
            if client_request != '':
                valid_http, resource = validate_http_request(client_request)
                if valid_http:
                    logging.info('Got a valid HTTP request')
                    handle_client_request(resource, client_socket, client_request)
                else:
                    logging.error('Error: Not a valid HTTP request')
                    handle_error(client_socket, INVALID_REQUEST_ERROR, "Bad Request")
                    break
            else:
                logging.error('Error: Sent empty message')
                # handle_error(client_socket, INVALID_REQUEST_ERROR, "Bad Request")
                break
    except socket.error as err:
        logging.error(f'Received socket exception: {err}')
    finally:
        # client_socket.close()
        logging.info('Closing connection')


def main():
    logging.basicConfig(filename="server.log", level=logging.DEBUG)
    # Open a socket and loop forever while waiting for clients
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        print("Listening for connections on port %d" % PORT)
        while True:
            client_socket, client_address = server_socket.accept()
            try:
                logging.info('New connection received')
                client_socket.settimeout(SOCKET_TIMEOUT)
                handle_client(client_socket)
            except socket.error as err:
                logging.error('received socket exception - ' + str(err))
            finally:
                client_socket.close()
    except socket.error as err:
        logging.error('received socket exception - ' + str(err))
    finally:
        server_socket.close()


if __name__ == "__main__":
    assert INVALID_REQUEST_ERROR == 400
    assert FILE_NOT_FOUND_ERROR == 404
    assert FORBIDDEN_ERROR == 403
    assert INTERNAL_SERVER_ERROR == 500
    # assert validate_http_request('GET /index.html HTTP/1.1\r\n') == (True, '/index.html')
    # assert validate_http_request('POST /index.html HTTP/1.1\r\n') == (False, '')
    assert get_content_type('html') == 'text/html;charset=utf-8'
    assert get_content_type('jpg') == 'image/jpeg'
    assert get_content_type('css') == 'text/css'
    assert get_content_type('js') == 'text/javascript; charset=UTF-8'
    assert get_content_type('txt') == 'text/plain'
    assert get_content_type('ico') == 'image/x-icon'
    assert get_content_type('gif') == 'image/jpeg'  # Assuming image type should be 'image/jpeg'
    assert get_content_type('png') == 'image/png'
    assert get_content_type('unknown') == 'application/octet-stream'
    main()
