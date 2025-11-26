package typerr.controller.data_forms;

public record TimestampEntry(
        String key,
        long timestamp,
        boolean correct
) {}
