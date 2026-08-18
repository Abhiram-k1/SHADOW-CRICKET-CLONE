import 'package:flutter/material.dart';
import '../models/analysis_result.dart';

class ResultScreen extends StatelessWidget {
  final AnalysisResult result;

  const ResultScreen({super.key, required this.result});

  Widget _buildScoreCard(String title, double score) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text('${score.toStringAsFixed(1)} / 100',
                 style: const TextStyle(fontSize: 18, color: Colors.blueAccent)),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (result.status == 'failed') {
      return Scaffold(
        appBar: AppBar(title: const Text('Analysis Failed')),
        body: const Center(child: Text('We could not analyze this image. Please ensure a full body is visible.')),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Analysis Result')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Primary Prediction
            if (result.prediction != null) ...[
              const Text("Detected Shot", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              Card(
                color: Colors.blue.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Text(
                    result.prediction!.shotClass.toUpperCase().replaceAll('_', ' '),
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.blue),
                    textAlign: TextAlign.center,
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],

            // Score Cards
            if (result.scores != null) ...[
              const Text("Posture Scores", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                childAspectRatio: 1.5,
                crossAxisSpacing: 10,
                mainAxisSpacing: 10,
                children: [
                  _buildScoreCard('Balance', result.scores!.balance),
                  _buildScoreCard('Alignment', result.scores!.alignment),
                  _buildScoreCard('Stance', result.scores!.stance),
                  _buildScoreCard('Power (Proxy)*', result.scores!.powerProxy),
                ],
              ),
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 8.0),
                child: Text(
                  "* Power Proxy is an estimate based on posture, not a physical measurement of energy.",
                  style: TextStyle(fontStyle: FontStyle.italic, fontSize: 12, color: Colors.grey),
                ),
              ),
              const SizedBox(height: 20),
            ],

            // Recommendations
            if (result.recommendations.isNotEmpty) ...[
              const Text("Top Recommendations", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              ...result.recommendations.map((rec) => ListTile(
                leading: const Icon(Icons.tips_and_updates, color: Colors.orange),
                title: Text(rec.text),
                subtitle: Text(rec.category),
              )).toList(),
            ]
          ],
        ),
      ),
    );
  }
}
