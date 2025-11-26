package typerr.model;

import jakarta.persistence.*;
import lombok.Data;

@Entity
@Data
public class TestResultTimestamp {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(nullable = false)
    private TestResult testResult;

    @Column(nullable = false)
    private String key;

    @Column(nullable = false)
    private long timestamp;

    @Column(nullable = false)
    private boolean correct;
}

