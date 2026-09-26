import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:aihub/views/chat/widgets/tool_shortcut_chips.dart';

void main() {
  testWidgets('ToolShortcutChips renders chips and handles selection', (tester) async {
    String? selectedQuery;

    tester.view.physicalSize = const Size(1200, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ToolShortcutChips(
            onSelectShortcut: (query) {
              selectedQuery = query;
            },
          ),
        ),
      ),
    );

    // Verify chips are rendered
    expect(find.text('Weather Bangalore'), findsOneWidget);
    expect(find.text('Crypto Summary'), findsOneWidget);
    expect(find.text('50K INR to USD'), findsOneWidget);
    expect(find.text('Market Data'), findsOneWidget);
    expect(find.text('Latest News'), findsOneWidget);

    // Tap on 'Weather Bangalore'
    await tester.tap(find.text('Weather Bangalore'));
    await tester.pump();

    // Verify callback was invoked with expected query
    expect(selectedQuery, 'What is the weather in Bangalore tomorrow?');
  });
}
