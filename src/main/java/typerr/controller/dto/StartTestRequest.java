package typerr.controller.dto;

public record StartTestRequest(
        Integer relevantWordCount,
        Integer totalWordCount,
        Integer lastN
) {}
