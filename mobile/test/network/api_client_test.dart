import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:aihub/core/network/api_client.dart';
import 'package:aihub/core/network/network_exceptions.dart';

void main() {
  group('ApiClient Tests', () {
    test('get returns decoded JSON on 200 OK', () async {
      final mockClient = MockClient((request) async {
        expect(request.method, 'GET');
        expect(request.url.toString(), 'http://localhost:8000/api/v1/tools');
        return http.Response(jsonEncode({'status': 'ok', 'count': 5}), 200);
      });

      final apiClient = ApiClient(client: mockClient);
      final result = await apiClient.get('http://localhost:8000/api/v1/tools');

      expect(result['status'], 'ok');
      expect(result['count'], 5);
    });

    test('post encodes body and decodes JSON response', () async {
      final mockClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.headers['Content-Type'], contains('application/json'));
        final body = jsonDecode(request.body);
        expect(body['message'], 'Hello');

        return http.Response(
          jsonEncode({'response': 'Hi there!', 'tool_calls': []}),
          200,
        );
      });

      final apiClient = ApiClient(client: mockClient);
      final result = await apiClient.post(
        'http://localhost:8000/api/v1/chat',
        {'message': 'Hello'},
      );

      expect(result['response'], 'Hi there!');
    });

    test('throws ServerException on 404 with error detail', () async {
      final mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode({'detail': 'Conversation not found'}),
          404,
        );
      });

      final apiClient = ApiClient(client: mockClient);

      expect(
        () => apiClient.get('http://localhost:8000/api/v1/chat/history/invalid'),
        throwsA(
          isA<ServerException>()
              .having((e) => e.statusCode, 'statusCode', 404)
              .having((e) => e.message, 'message', 'Conversation not found'),
        ),
      );
    });

    test('throws ConnectionException on SocketException', () async {
      final mockClient = MockClient((request) async {
        throw const SocketException('Failed host lookup');
      });

      final apiClient = ApiClient(client: mockClient);

      expect(
        () => apiClient.get('http://nonexistent-host:8000/health'),
        throwsA(isA<ConnectionException>()),
      );
    });
  });
}
