import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'network_exceptions.dart';

class ApiClient {
  final http.Client _client;
  static const Duration defaultTimeout = Duration(seconds: 15);

  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  Future<dynamic> get(String url) async {
    try {
      final response = await _client
          .get(
            Uri.parse(url),
            headers: {'Accept': 'application/json'},
          )
          .timeout(defaultTimeout);

      return _handleResponse(response);
    } on SocketException {
      throw ConnectionException();
    } on TimeoutException {
      throw TimeoutException();
    } catch (e) {
      if (e is NetworkException) rethrow;
      throw NetworkException('Unexpected network error: $e');
    }
  }

  Future<dynamic> post(String url, Map<String, dynamic> body) async {
    try {
      final response = await _client
          .post(
            Uri.parse(url),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: jsonEncode(body),
          )
          .timeout(defaultTimeout);

      return _handleResponse(response);
    } on SocketException {
      throw ConnectionException();
    } on TimeoutException {
      throw TimeoutException();
    } catch (e) {
      if (e is NetworkException) rethrow;
      throw NetworkException('Unexpected network error: $e');
    }
  }

  Future<dynamic> delete(String url) async {
    try {
      final response = await _client
          .delete(
            Uri.parse(url),
            headers: {'Accept': 'application/json'},
          )
          .timeout(defaultTimeout);

      return _handleResponse(response);
    } on SocketException {
      throw ConnectionException();
    } on TimeoutException {
      throw TimeoutException();
    } catch (e) {
      if (e is NetworkException) rethrow;
      throw NetworkException('Unexpected network error: $e');
    }
  }

  dynamic _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return null;
      return jsonDecode(utf8.decode(response.bodyBytes));
    }

    try {
      final errBody = jsonDecode(utf8.decode(response.bodyBytes));
      final detail = errBody['detail'] ?? errBody['message'] ?? 'Server error';
      throw ServerException(detail.toString(), response.statusCode);
    } catch (e) {
      if (e is ServerException) rethrow;
      throw ServerException(
        'Request failed with status: ${response.statusCode}',
        response.statusCode,
      );
    }
  }

  void dispose() {
    _client.close();
  }
}
