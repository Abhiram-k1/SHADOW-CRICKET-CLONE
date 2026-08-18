class Prediction {
  final String stanceClass;
  final String shotClass;
  final double confidence;

  Prediction({required this.stanceClass, required this.shotClass, required this.confidence});

  factory Prediction.fromJson(Map<String, dynamic> json) {
    return Prediction(
      stanceClass: json['stance_class'] ?? '',
      shotClass: json['shot_class'] ?? '',
      confidence: (json['confidence'] ?? 0.0).toDouble(),
    );
  }
}

class Scores {
  final double balance;
  final double alignment;
  final double stance;
  final double powerProxy;

  Scores({required this.balance, required this.alignment, required this.stance, required this.powerProxy});

  factory Scores.fromJson(Map<String, dynamic> json) {
    return Scores(
      balance: (json['balance'] ?? 0.0).toDouble(),
      alignment: (json['alignment'] ?? 0.0).toDouble(),
      stance: (json['stance'] ?? 0.0).toDouble(),
      powerProxy: (json['power_proxy'] ?? 0.0).toDouble(),
    );
  }
}

class Recommendation {
  final String text;
  final String category;

  Recommendation({required this.text, required this.category});

  factory Recommendation.fromJson(Map<String, dynamic> json) {
    return Recommendation(
      text: json['text'] ?? '',
      category: json['category'] ?? '',
    );
  }
}

class AnalysisResult {
  final String id;
  final String status;
  final Prediction? prediction;
  final Scores? scores;
  final List<Recommendation> recommendations;

  AnalysisResult({
    required this.id,
    required this.status,
    this.prediction,
    this.scores,
    required this.recommendations,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    var recsFromJson = json['recommendations'] as List? ?? [];
    List<Recommendation> recList = recsFromJson.map((i) => Recommendation.fromJson(i)).toList();

    return AnalysisResult(
      id: json['id'],
      status: json['status'],
      prediction: json['prediction'] != null ? Prediction.fromJson(json['prediction']) : null,
      scores: json['scores'] != null ? Scores.fromJson(json['scores']) : null,
      recommendations: recList,
    );
  }
}
