package typerr.controller.data_forms;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.util.List;

public record TestDataRequest(
        String target,
        String typed,
        int time,
        double wpm,
        double accuracy,
        @JsonProperty("timestamps_firsts")
        List<TimestampEntry> timestampsFirsts
) {}