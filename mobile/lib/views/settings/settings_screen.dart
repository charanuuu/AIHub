import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/api_endpoints.dart';
import '../../core/constants/app_colors.dart';
import '../../providers/settings_provider.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _urlController;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(
      text: context.read<SettingsProvider>().backendUrl,
    );
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  void _saveUrl() {
    final newUrl = _urlController.text.trim();
    if (newUrl.isNotEmpty) {
      context.read<SettingsProvider>().setBackendUrl(newUrl);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Backend URL updated & checking connection...')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Connection Status Card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        settings.isBackendOnline
                            ? Icons.check_circle_rounded
                            : Icons.error_outline_rounded,
                        color: settings.isBackendOnline
                            ? AppColors.success
                            : AppColors.error,
                      ),
                      const SizedBox(width: 10),
                      Text(
                        settings.isBackendOnline
                            ? 'Backend Connected'
                            : 'Backend Offline',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: settings.isBackendOnline
                              ? AppColors.success
                              : AppColors.error,
                        ),
                      ),
                      const Spacer(),
                      if (settings.isChecking)
                        const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      else
                        TextButton(
                          onPressed: () => settings.checkBackendHealth(),
                          child: const Text('Test Connection'),
                        ),
                    ],
                  ),
                  if (settings.isBackendOnline) ...[
                    const SizedBox(height: 8),
                    Text(
                      'App Version: ${settings.backendVersion ?? "1.0.0"} · Active Tools: ${settings.activeToolsCount}',
                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Backend URL Configuration
          const Text(
            'BACKEND CONFIGURATION',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.1,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextField(
                    controller: _urlController,
                    decoration: const InputDecoration(
                      labelText: 'FastAPI Backend URL',
                      helperText: 'Host where your Python backend is running',
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      OutlinedButton(
                        onPressed: () {
                          _urlController.text = ApiEndpoints.defaultBaseUrl;
                          _saveUrl();
                        },
                        child: const Text('Emulator (10.0.2.2)'),
                      ),
                      const SizedBox(width: 8),
                      OutlinedButton(
                        onPressed: () {
                          _urlController.text = ApiEndpoints.localhostBaseUrl;
                          _saveUrl();
                        },
                        child: const Text('Localhost (127.0.0.1)'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: _saveUrl,
                    child: const Text('Apply Changes'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Appearance
          const Text(
            'APPEARANCE',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.1,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 8),
          Card(
            child: SwitchListTile(
              secondary: Icon(
                settings.isDarkMode ? Icons.dark_mode_rounded : Icons.light_mode_rounded,
              ),
              title: const Text('Dark Mode'),
              subtitle: Text(settings.isDarkMode ? 'Dark theme enabled' : 'Light theme enabled'),
              value: settings.isDarkMode,
              onChanged: (_) => settings.toggleTheme(),
            ),
          ),
          const SizedBox(height: 20),

          // Architecture & Security
          const Text(
            'ARCHITECTURE & SECURITY',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 1.1,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 8),
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '🔒 Zero Secrets in Flutter',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'All 3rd-party API keys (OpenAI, Weather, etc.) are strictly kept on the FastAPI backend.',
                    style: TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                  SizedBox(height: 10),
                  Text(
                    '⚡ Strict Tool Schemas',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'AI agent cannot invent live data. Queries requiring real-time facts execute validated tools.',
                    style: TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
