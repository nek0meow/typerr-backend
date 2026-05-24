package typerr.controller.dto;

import java.util.Date;

public record TestResultSimpleData(
    Long id,
    double wpm,
    double time,
    Date savedAt
) {}
