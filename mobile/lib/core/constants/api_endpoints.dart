class ApiEndpoints {
  // 10.0.2.2 is the default Android emulator alias for host machine's localhost (127.0.0.1)
  // For physical Android device or local debugging, configure in SettingsScreen
  static const String defaultBaseUrl = 'http://10.0.2.2:8000';
  static const String localhostBaseUrl = 'http://127.0.0.1:8000';

  static const String apiV1Prefix = '/api/v1';

  static String health(String baseUrl) => '$baseUrl$apiV1Prefix/health';
  static String tools(String baseUrl) => '$baseUrl$apiV1Prefix/tools';
  static String weatherTool(String baseUrl) => '$baseUrl$apiV1Prefix/tools/weather';
  static String chat(String baseUrl) => '$baseUrl$apiV1Prefix/chat';
  static String conversations(String baseUrl) => '$baseUrl$apiV1Prefix/chat/conversations';
  static String conversationMessages(String baseUrl, String id) =>
      '$baseUrl$apiV1Prefix/chat/conversations/$id/messages';
  static String deleteConversation(String baseUrl, String id) =>
      '$baseUrl$apiV1Prefix/chat/conversations/$id';
}
