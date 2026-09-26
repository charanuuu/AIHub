import 'package:flutter_test/flutter_test.dart';
import 'package:aihub/core/network/session_manager.dart';

void main() {
  group('SessionManager Tests', () {
    setUp(() {
      SessionManager.resetForTesting();
    });

    tearDown(() {
      SessionManager.resetForTesting();
    });

    test('generateSecureUuid generates valid RFC 4122 UUID v4', () {
      final uuid = SessionManager.generateSecureUuid();
      expect(uuid.length, 36);

      // Verify format 8-4-4-4-12
      final parts = uuid.split('-');
      expect(parts.length, 5);
      expect(parts[0].length, 8);
      expect(parts[1].length, 4);
      expect(parts[2].length, 4);
      expect(parts[3].length, 4);
      expect(parts[4].length, 12);

      // Verify version 4
      expect(parts[2].startsWith('4'), isTrue);
      // Verify variant (8, 9, a, or b)
      expect(['8', '9', 'a', 'b', 'A', 'B'].contains(parts[3][0]), isTrue);
    });

    test('generateSecureUuid produces unique random values', () {
      final id1 = SessionManager.generateSecureUuid();
      final id2 = SessionManager.generateSecureUuid();
      expect(id1, isNot(equals(id2)));
    });

    test('getSessionId persists across multiple calls in the same session', () {
      final id1 = SessionManager.getSessionId();
      final id2 = SessionManager.getSessionId();
      expect(id1, equals(id2));
    });

    test('resetForTesting overrides session ID with custom value', () {
      const customId = '12345678-1234-4234-8234-123456789abc';
      SessionManager.resetForTesting(customId);
      expect(SessionManager.getSessionId(), equals(customId));
    });
  });
}
