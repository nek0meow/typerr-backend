package typerr.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import typerr.model.TestResultTimestamp;

import java.util.List;

@Repository
public interface TestResultTimestampRepository extends JpaRepository<TestResultTimestamp, Long> {
    List<TestResultTimestamp> findByTestResultId(Long testResultId);
}
