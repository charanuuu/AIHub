import 'package:flutter/foundation.dart';
import '../core/constants/api_endpoints.dart';
import '../core/network/api_client.dart';
import '../models/tool_status.dart';

class ToolsProvider with ChangeNotifier {
  final ApiClient _apiClient = ApiClient();

  List<ToolStatus> _tools = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<ToolStatus> get tools => _tools;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  List<ToolStatus> get activeTools => _tools.where((t) => t.isActive).toList();

  Future<void> fetchTools(String baseUrl) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final response = await _apiClient.get(ApiEndpoints.tools(baseUrl));
      if (response is List) {
        _tools = response
            .map((item) => ToolStatus.fromJson(Map<String, dynamic>.from(item)))
            .toList();
      }
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  @override
  void dispose() {
    _apiClient.dispose();
    super.dispose();
  }
}
