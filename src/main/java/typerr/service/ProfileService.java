package typerr.service;


import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import typerr.controller.dto.TestResultSimpleData;
import typerr.model.TestResult;
import typerr.repository.TestResultRepository;

import java.util.List;

@Service
public class ProfileService {

    @Autowired
    private TestResultRepository testResultRepository;

    public List<TestResultSimpleData> getUserTestData(Long userId) {
        List<TestResult> results = testResultRepository.findByUserId(userId);
        return results.stream()
                .map(r -> new TestResultSimpleData(
                        r.getId(),
                        r.getWpm(),
                        r.getAccuracy(),
                        r.getTime(),
                        r.getSavedAt()
                ))
                .toList();
    }
}
