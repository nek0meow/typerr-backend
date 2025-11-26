package typerr.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import typerr.controller.data_forms.TestDataRequest;
import typerr.model.TestResult;
import typerr.model.TestResultTimestamp;
import typerr.model.User;
import typerr.repository.TestResultRepository;
import typerr.repository.TestResultTimestampRepository;

import java.time.Instant;
import java.util.Date;
import java.util.List;
import java.util.Optional;

@Service
public class TestService {

    @Autowired
    private TestResultRepository testResultRepository;

    public void processTestResult(TestDataRequest data, User user) {
        TestResult result = new TestResult();
        result.setUser(user);
        result.setTarget(data.target());
        result.setTyped(data.typed());
        result.setTime(data.time());
        result.setWpm(data.wpm());
        result.setAccuracy(data.accuracy());
        result.setSavedAt(Date.from(Instant.now()));

        List<TestResultTimestamp> timestamps = Optional.ofNullable(data.timestampsFirsts())
                .orElse(List.of())
                .stream()
                .map(ts -> {
                    TestResultTimestamp trt = new TestResultTimestamp();
                    trt.setTestResult(result);
                    trt.setKey(ts.key());
                    trt.setTimestamp(ts.timestamp());
                    trt.setCorrect(ts.correct());
                    return trt;
                })
                .toList();

        result.setTimestampsFirsts(timestamps);
        testResultRepository.save(result);

        long count = testResultRepository.countByUser(user);
        int excess = (int) (count - 100);

        if (excess > 0) {
            List<TestResult> oldTests = testResultRepository.findTopByUserOrderByIdAsc(
                    user,
                    PageRequest.of(0, excess)
            );
            testResultRepository.deleteAll(oldTests);
        }
    }
}
