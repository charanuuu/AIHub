import 'package:flutter/foundation.dart';
import '../core/constants/api_endpoints.dart';
import '../core/network/api_client.dart';

class SettingsProvider with ChangeNotifier {
  final ApiClient _apiClient = ApiClient();

  String _backendUrl = ApiEndpoints.defaultBaseUrl;
  bool _isDarkMode = true;
  bool _isBackendOnline = false;
  bool _isChecking = false;
  String? _backendVersion;
  int _activeToolsCount = 0;

  String get backendUrl => _backendUrl;
  bool get isDarkMode => _isDarkMode;
  bool get isBackendOnline => _isBackendOnline;
  bool get isChecking => _isChecking;
  String? get backendVersion => _backendVersion;
  int get activeToolsCount => _activeToolsCount;

  void setBackendUrl(String url) {
    if (url.trim().isNotEmpty) {
      _backendUrl = url.trim().replaceAll(RegExp(r'/+$'), '');
      notifyListeners();
      checkBackendHealth();
    }
  }

  void toggleTheme() {
    _isDarkMode = !_isDarkMode;
    notifyListeners();
  }

  Future<void> checkBackendHealth() async {
    _isChecking = true;
    notifyListeners();

    try {
      final response = await _apiClient.get(ApiEndpoints.health(_backendUrl));
      if (response != null && response is Map) {
        _isBackendOnline = response['status'] == 'healthy' || response['status'] == 'degraded';
        _backendVersion = response['version'];
        _activeToolsCount = response['tools_count'] ?? 0;
      } else {
        _isBackendOnline = false;
      }
    } catch (_) {
      _isBackendOnline = false;
    } finally {
      _isChecking = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _apiClient.dispose();
    super.dispose();
  }
}
