package typerr.controller.dto;

public record TimestampEntry(
        String key,
        long timestamp,
        boolean correct
) {}
