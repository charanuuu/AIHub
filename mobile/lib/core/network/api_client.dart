import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'network_exceptions.dart';
import 'session_manager.dart';

class ApiClient {
  final http.Client _client;
  static const Duration defaultTimeout = Duration(seconds: 15);

  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  Map<String, String> _buildHeaders({Map<String, String>? additionalHeaders}) {
    return {
      'Accept': 'application/json',
      'X-Session-ID': SessionManager.getSessionId(),
      if (additionalHeaders != null) ...additionalHeaders,
    };
  }

  Future<dynamic> get(String url, {Map<String, String>? headers}) async {
    try {
      final response = await _client
          .get(
            Uri.parse(url),
            headers: _buildHeaders(additionalHeaders: headers),
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

  Future<dynamic> post(
    String url,
    Map<String, dynamic> body, {
    Map<String, String>? headers,
  }) async {
    try {
      final requestHeaders = _buildHeaders(
        additionalHeaders: {
          'Content-Type': 'application/json',
          if (headers != null) ...headers,
        },
      );

      final response = await _client
          .post(
            Uri.parse(url),
            headers: requestHeaders,
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

  Future<dynamic> delete(String url, {Map<String, String>? headers}) async {
    try {
      final response = await _client
          .delete(
            Uri.parse(url),
            headers: _buildHeaders(additionalHeaders: headers),
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
