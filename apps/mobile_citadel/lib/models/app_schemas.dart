
class QRSchema {
  final List<QRHandlerSchema> handlers;
  final List<String> drawers; // module styles
  final List<String> gradients;
  final List<String> eyeStyles;

  QRSchema({
    required this.handlers,
    required this.drawers,
    required this.gradients,
    required this.eyeStyles,
  });

  factory QRSchema.fromJson(Map<String, dynamic> json) {
    return QRSchema(
      handlers: (json['handlers'] as List)
          .map((e) => QRHandlerSchema.fromJson(e))
          .toList(),
      drawers: List<String>.from(json['drawers'] ?? []),
      gradients: List<String>.from(json['gradients'] ?? []),
      eyeStyles: List<String>.from(json['eye_styles'] ?? []),
    );
  }
}

class QRHandlerSchema {
  final String id;
  final String name;
  final String category;
  final String description;
  final List<QRParam> params;

  QRHandlerSchema({
    required this.id,
    required this.name,
    required this.category,
    required this.description,
    required this.params,
  });

  factory QRHandlerSchema.fromJson(Map<String, dynamic> json) {
    return QRHandlerSchema(
      id: json['id'],
      name: json['name'],
      category: json['category'],
      description: json['description'] ?? '',
      params: (json['params'] as List)
          .map((e) => QRParam.fromJson(e))
          .toList(),
    );
  }
}

class QRParam {
  final String name;
  final String type; // str, int, float, bool, color, file
  final dynamic defaultValue;
  final bool required;
  final List<String>? options;

  QRParam({
    required this.name,
    required this.type,
    this.defaultValue,
    required this.required,
    this.options,
  });

  factory QRParam.fromJson(Map<String, dynamic> json) {
    return QRParam(
      name: json['name'],
      type: json['type'],
      defaultValue: json['default'],
      required: json['required'] ?? false,
      options: json['options'] != null ? List<String>.from(json['options']) : null,
    );
  }
}

class ImageGenSchema {
  final List<String> styles;
  final Map<String, StyleDetails> styleDetails;
  final List<String> ratios;
  final List<String> schedulers;
  final List<String> controlTypes;

  ImageGenSchema({
    required this.styles,
    required this.styleDetails,
    required this.ratios,
    required this.schedulers,
    required this.controlTypes,
  });

  factory ImageGenSchema.fromJson(Map<String, dynamic> json) {
    var details = <String, StyleDetails>{};
    if (json['style_details'] != null) {
      (json['style_details'] as Map<String, dynamic>).forEach((k, v) {
        details[k] = StyleDetails.fromJson(v);
      });
    }
    return ImageGenSchema(
      styles: List<String>.from(json['styles'] ?? []),
      styleDetails: details,
      ratios: List<String>.from(json['ratios'] ?? []),
      schedulers: List<String>.from(json['schedulers'] ?? []),
      controlTypes: List<String>.from(json['control_types'] ?? []),
    );
  }
}

class StyleDetails {
  final String description;
  final List<String> types; // substyles

  StyleDetails({required this.description, required this.types});

  factory StyleDetails.fromJson(Map<String, dynamic> json) {
    return StyleDetails(
      description: json['description'] ?? '',
      types: List<String>.from(json['types'] ?? []),
    );
  }
}


class SurgeonSchema {
  final List<String> modes;
  final List<String> solidColors;
  final Map<String, List<String>> assets;

  SurgeonSchema({
    required this.modes,
    required this.solidColors,
    required this.assets,
  });

  factory SurgeonSchema.fromJson(Map<String, dynamic> json) {
     var assetsMap = <String, List<String>>{};
     if (json['assets'] != null) {
       (json['assets'] as Map<String, dynamic>).forEach((k, v) {
         assetsMap[k] = List<String>.from(v);
       });
     }
    return SurgeonSchema(
      modes: List<String>.from(json['modes'] ?? []),
      solidColors: List<String>.from(json['solid_colors'] ?? []),
      assets: assetsMap,
    );
  }
}

class NewspaperSchema {
  final List<String> regions;
  final List<String> styles;
  final List<String> magazineSubstyles;
  final List<String> languages;

  NewspaperSchema({
    required this.regions,
    required this.styles,
    required this.magazineSubstyles,
    required this.languages,
  });

  factory NewspaperSchema.fromJson(Map<String, dynamic> json) {
    return NewspaperSchema(
      regions: List<String>.from(json['regions'] ?? []),
      styles: List<String>.from(json['styles'] ?? []),
      magazineSubstyles: List<String>.from(json['magazine_substyles'] ?? []),
      languages: List<String>.from(json['languages'] ?? []),
    );
  }
}
