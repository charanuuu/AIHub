import 'package:flutter_test/flutter_test.dart';
import 'package:aihub/models/tool_status.dart';

void main() {
  group('ToolStatus Tests', () {
    test('fromJson parses active tool correctly', () {
      final json = {
        'name': 'get_weather',
        'category': 'Weather',
        'description': 'Real-time weather info',
        'status': 'active',
        'provider': 'Open-Meteo',
      };

      final tool = ToolStatus.fromJson(json);

      expect(tool.name, 'get_weather');
      expect(tool.category, 'Weather');
      expect(tool.description, 'Real-time weather info');
      expect(tool.status, 'active');
      expect(tool.provider, 'Open-Meteo');
      expect(tool.isActive, isTrue);
    });

    test('isActive returns false when status is planned', () {
      final json = {
        'name': 'future_tool',
        'status': 'planned',
      };

      final tool = ToolStatus.fromJson(json);

      expect(tool.isActive, isFalse);
    });
  });
}
