package typerr.controller.dto;

import java.util.List;

public record StartTestResponse(
        String text,
        List<String> relevantWords,
        List<String> fillerWords
) {}
