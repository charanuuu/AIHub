import 'package:flutter_test/flutter_test.dart';
import 'package:aihub/models/chat_message.dart';

void main() {
  group('ToolCallInfo Tests', () {
    test('fromJson parses complete valid JSON payload', () {
      final json = {
        'tool_name': 'get_weather',
        'arguments': {'city': 'Bangalore'},
        'result': {'temperature': 24.5, 'condition': 'Clear'},
        'success': true,
        'error': null,
        'execution_time_ms': 142.5,
      };

      final info = ToolCallInfo.fromJson(json);

      expect(info.toolName, 'get_weather');
      expect(info.arguments['city'], 'Bangalore');
      expect(info.result?['temperature'], 24.5);
      expect(info.success, isTrue);
      expect(info.error, isNull);
      expect(info.executionTimeMs, 142.5);
    });

    test('fromJson handles null and missing optional fields with safe defaults', () {
      final json = <String, dynamic>{};

      final info = ToolCallInfo.fromJson(json);

      expect(info.toolName, 'unknown_tool');
      expect(info.arguments, isEmpty);
      expect(info.result, isNull);
      expect(info.success, isTrue);
      expect(info.error, isNull);
      expect(info.executionTimeMs, 0.0);
    });
  });

  group('ChatMessage Tests', () {
    test('user factory creates user message with timestamp', () {
      final message = ChatMessage.user('Hello Assistant');

      expect(message.isUser, isTrue);
      expect(message.role, 'user');
      expect(message.content, 'Hello Assistant');
      expect(message.hasTools, isFalse);
      expect(message.isError, isFalse);
      expect(message.id, isNotEmpty);
    });

    test('assistant factory creates assistant message with tools', () {
      final toolCall = ToolCallInfo(
        toolName: 'convert_currency',
        arguments: {'from': 'USD', 'to': 'INR', 'amount': 100},
        success: true,
      );

      final message = ChatMessage.assistant(
        id: 'msg-123',
        content: '100 USD is approx 8,300 INR',
        toolCalls: [toolCall],
      );

      expect(message.isUser, isFalse);
      expect(message.role, 'assistant');
      expect(message.content, contains('8,300 INR'));
      expect(message.hasTools, isTrue);
      expect(message.toolCalls.length, 1);
      expect(message.toolCalls.first.toolName, 'convert_currency');
      expect(message.isError, isFalse);
    });

    test('error factory creates error flagged assistant message', () {
      final message = ChatMessage.error('Network failure');

      expect(message.isUser, isFalse);
      expect(message.role, 'assistant');
      expect(message.isError, isTrue);
      expect(message.content, 'Network failure');
      expect(message.hasTools, isFalse);
    });
  });
}
