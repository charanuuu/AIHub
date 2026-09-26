import 'package:flutter_test/flutter_test.dart';
import 'package:aihub/models/conversation.dart';

void main() {
  group('ConversationSummary Tests', () {
    test('fromJson correctly parses complete JSON', () {
      final json = {
        'id': 'conv-456',
        'title': 'Market Analysis',
        'created_at': '2026-09-25T10:00:00Z',
        'updated_at': '2026-09-25T10:15:00Z',
        'message_count': 6,
      };

      final conv = ConversationSummary.fromJson(json);

      expect(conv.id, 'conv-456');
      expect(conv.title, 'Market Analysis');
      expect(conv.messageCount, 6);
      expect(conv.createdAt.year, 2026);
    });

    test('fromJson provides safe defaults for null or missing fields', () {
      final json = <String, dynamic>{};

      final conv = ConversationSummary.fromJson(json);

      expect(conv.id, isEmpty);
      expect(conv.title, 'New Conversation');
      expect(conv.messageCount, 0);
      expect(conv.createdAt, isA<DateTime>());
      expect(conv.updatedAt, isA<DateTime>());
    });
  });
}
