import 'package:flutter_test/flutter_test.dart';
import 'package:aihub/providers/settings_provider.dart';

void main() {
  group('SettingsProvider Tests', () {
    test('initializes with default backend URL and dark mode', () {
      final provider = SettingsProvider();

      expect(provider.backendUrl, isNotEmpty);
      expect(provider.isDarkMode, isTrue);
      expect(provider.isBackendOnline, isFalse);
    });

    test('toggleTheme alternates between dark and light mode', () {
      final provider = SettingsProvider();

      expect(provider.isDarkMode, isTrue);
      provider.toggleTheme();
      expect(provider.isDarkMode, isFalse);
      provider.toggleTheme();
      expect(provider.isDarkMode, isTrue);
    });

    test('setBackendUrl trims whitespace and trailing slashes', () {
      final provider = SettingsProvider();

      provider.setBackendUrl('  http://192.168.1.50:8000///  ');
      expect(provider.backendUrl, 'http://192.168.1.50:8000');
    });
  });
}
