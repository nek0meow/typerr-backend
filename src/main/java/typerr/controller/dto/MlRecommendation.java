package typerr.controller.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public record MlRecommendation(
        String word,
        double score,
        double frequency,
        String matched_trigrams
) {}
