package typerr.controller.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

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