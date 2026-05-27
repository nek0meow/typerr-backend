package typerr.repository;


import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import typerr.model.TestResult;
import typerr.model.User;

import java.util.List;

public interface TestResultRepository extends JpaRepository<TestResult, Long> {

    long countByUser(User user);

    // get oldest N tests
    @Query("SELECT t FROM TestResult t WHERE t.user = :user ORDER BY t.id ASC")
    List<TestResult> findTopByUserOrderByIdAsc(@Param("user") User user, Pageable pageable);
    @Query("SELECT t FROM TestResult t WHERE t.user = :user ORDER BY t.savedAt DESC, t.id DESC")
    List<TestResult> findRecentByUser(@Param("user") User user, Pageable pageable);
    List<TestResult> findByUserId(Long userId);
    List<TestResult> findByUserIdOrderByIdDesc(Long userId);
}
