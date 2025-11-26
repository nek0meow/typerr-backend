package typerr.controller.data_forms;

import java.util.Date;

public record TestResultSimpleData(
    Long id,
    double wpm,
    double time,
    Date savedAt
) {}
