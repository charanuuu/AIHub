class NetworkException implements Exception {
  final String message;
  final int? statusCode;

  NetworkException(this.message, [this.statusCode]);

  @override
  String toString() => message;
}

class ConnectionException extends NetworkException {
  ConnectionException([super.message = 'Cannot connect to AI Hub backend server. Please verify backend URL.']);
}

class TimeoutException extends NetworkException {
  TimeoutException([super.message = 'The request timed out. Please check your network connection.']);
}

class ServerException extends NetworkException {
  ServerException(super.message, [super.statusCode]);
}
