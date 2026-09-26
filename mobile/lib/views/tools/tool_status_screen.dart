import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../models/tool_status.dart';
import '../../providers/settings_provider.dart';
import '../../providers/tools_provider.dart';
import '../../core/network/api_client.dart';
import '../../core/constants/api_endpoints.dart';

class ToolStatusScreen extends StatefulWidget {
  const ToolStatusScreen({super.key});

  @override
  State<ToolStatusScreen> createState() => _ToolStatusScreenState();
}

class _ToolStatusScreenState extends State<ToolStatusScreen> {
  final ApiClient _apiClient = ApiClient();
  bool _testingWeather = false;
  String? _weatherTestResult;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final backendUrl = context.read<SettingsProvider>().backendUrl;
      context.read<ToolsProvider>().fetchTools(backendUrl);
    });
  }

  Color _getCategoryColor(String category) {
    switch (category.toLowerCase()) {
      case 'weather':
        return AppColors.toolWeather;
      case 'cryptocurrency':
      case 'crypto':
        return AppColors.toolCrypto;
      case 'currency':
        return AppColors.toolCurrency;
      case 'finance':
        return AppColors.toolFinance;
      case 'news':
        return AppColors.toolNews;
      default:
        return AppColors.accent;
    }
  }

  Future<void> _runWeatherTest() async {
    final backendUrl = context.read<SettingsProvider>().backendUrl;
    setState(() {
      _testingWeather = true;
      _weatherTestResult = null;
    });

    try {
      final result = await _apiClient.post(
        ApiEndpoints.weatherTool(backendUrl),
        {'city': 'Bangalore', 'days': 1, 'unit': 'celsius'},
      );

      if (result != null && result is Map) {
        final cur = result['data']?['current'];
        final temp = cur?['temperature'];
        final cond = cur?['condition'];
        setState(() {
          _weatherTestResult =
              'Success! Live Bangalore weather: $temp°C, $cond (via ${result['provider']})';
        });
      }
    } catch (e) {
      setState(() {
        _weatherTestResult = 'Test failed: $e';
      });
    } finally {
      setState(() {
        _testingWeather = false;
      });
    }
  }

  @override
  void dispose() {
    _apiClient.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final toolsProvider = context.watch<ToolsProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tools & Providers'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () {
              final backendUrl = context.read<SettingsProvider>().backendUrl;
              toolsProvider.fetchTools(backendUrl);
            },
          ),
        ],
      ),
      body: toolsProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Live test banner for Weather tool
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: AppColors.toolWeather.withValues(alpha: 0.2),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(
                                Icons.wb_sunny_rounded,
                                color: AppColors.toolWeather,
                                size: 20,
                              ),
                            ),
                            const SizedBox(width: 12),
                            const Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Live Weather Tool Test',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 15,
                                    ),
                                  ),
                                  Text(
                                    'Direct test of Open-Meteo external provider',
                                    style: TextStyle(fontSize: 12, color: Colors.grey),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.toolWeather,
                            foregroundColor: Colors.white,
                          ),
                          icon: _testingWeather
                              ? const SizedBox(
                                  width: 14,
                                  height: 14,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor: AlwaysStoppedAnimation(Colors.white),
                                  ),
                                )
                              : const Icon(Icons.play_arrow_rounded, size: 18),
                          label: Text(_testingWeather ? 'Testing...' : 'Test Bangalore Weather'),
                          onPressed: _testingWeather ? null : _runWeatherTest,
                        ),
                        if (_weatherTestResult != null) ...[
                          const SizedBox(height: 10),
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: _weatherTestResult!.contains('Success')
                                  ? AppColors.success.withValues(alpha: 0.15)
                                  : AppColors.error.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              _weatherTestResult!,
                              style: TextStyle(
                                fontSize: 12,
                                color: _weatherTestResult!.contains('Success')
                                    ? AppColors.success
                                    : AppColors.error,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  'REGISTERED TOOLS & PIPELINE',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1.1,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 8),
                for (final tool in toolsProvider.tools)
                  _buildToolCard(tool, isDark),
              ],
            ),
    );
  }

  Widget _buildToolCard(ToolStatus tool, bool isDark) {
    final catColor = _getCategoryColor(tool.category);

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Chip(
                  label: Text(
                    tool.category,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: catColor,
                    ),
                  ),
                  backgroundColor: catColor.withValues(alpha: 0.15),
                  side: BorderSide.none,
                  padding: EdgeInsets.zero,
                  visualDensity: VisualDensity.compact,
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: tool.isActive
                        ? AppColors.success.withValues(alpha: 0.15)
                        : Colors.grey.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    tool.isActive ? 'Active' : 'Planned',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: tool.isActive ? AppColors.success : Colors.grey,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              tool.name,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 15,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              tool.description,
              style: TextStyle(
                fontSize: 12,
                color: isDark ? Colors.white70 : Colors.black87,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Provider: ${tool.provider}',
              style: const TextStyle(
                fontSize: 11,
                color: Colors.grey,
                fontFamily: 'monospace',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
