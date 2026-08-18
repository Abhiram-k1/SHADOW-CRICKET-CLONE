import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shadow_cricket_app/main.dart';

void main() {
  testWidgets('App renders Home Screen', (WidgetTester tester) async {
    await tester.pumpWidget(const ShadowCricketApp());
    expect(find.text('Welcome to Shadow Cricket AI'), findsOneWidget);
    expect(find.byType(ElevatedButton), findsOneWidget);
  });
}
