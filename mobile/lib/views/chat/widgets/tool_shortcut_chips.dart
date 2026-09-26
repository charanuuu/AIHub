import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';

class ToolShortcutChips extends StatelessWidget {
  final Function(String query) onSelectShortcut;

  const ToolShortcutChips({
    super.key,
    required this.onSelectShortcut,
  });

  static const List<Map<String, dynamic>> shortcuts = [
    {
      'label': 'Weather Bangalore',
      'query': 'What is the weather in Bangalore tomorrow?',
      'icon': Icons.wb_sunny_rounded,
      'color': AppColors.toolWeather,
    },
    {
      'label': 'Crypto Summary',
      'query': "Give me today's crypto market summary.",
      'icon': Icons.currency_bitcoin_rounded,
      'color': AppColors.toolCrypto,
    },
    {
      'label': '50K INR to USD',
      'query': 'Convert 50,000 INR to USD.',
      'icon': Icons.currency_exchange_rounded,
      'color': AppColors.toolCurrency,
    },
    {
      'label': 'Market Data',
      'query': 'What are the top market indices today?',
      'icon': Icons.trending_up_rounded,
      'color': AppColors.toolFinance,
    },
    {
      'label': 'Latest News',
      'query': 'What is the top technology news today?',
      'icon': Icons.newspaper_rounded,
      'color': AppColors.toolNews,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 44,
      child: ListView.separated(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        scrollDirection: Axis.horizontal,
        itemCount: shortcuts.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final item = shortcuts[index];
          final Color color = item['color'];

          return ActionChip(
            avatar: Icon(item['icon'] as IconData, size: 16, color: color),
            label: Text(
              item['label'] as String,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: Theme.of(context).brightness == Brightness.dark
                    ? Colors.white.withValues(alpha: 0.9)
                    : Colors.black87,
              ),
            ),
            backgroundColor: color.withValues(alpha: 0.12),
            side: BorderSide(color: color.withValues(alpha: 0.3), width: 1),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
            onPressed: () => onSelectShortcut(item['query'] as String),
          );
        },
      ),
    );
  }
}
