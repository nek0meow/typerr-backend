package typerr.service;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.validation.constraints.Max;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import typerr.controller.dto.MlRecommendation;
import typerr.controller.dto.StartTestRequest;
import typerr.controller.dto.StartTestResponse;
import typerr.controller.dto.TestDataRequest;
import typerr.model.TestResult;
import typerr.model.TestResultTimestamp;
import typerr.model.User;
import typerr.repository.TestResultRepository;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Random;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Service
public class TestService {

    private static final Pattern WORD_PATTERN = Pattern.compile("[a-z]+");
    private static final int DEFAULT_RELEVANT_WORD_COUNT = 8;
    private static final int DEFAULT_TOTAL_WORD_COUNT = 30;
    private static final int DEFAULT_LAST_N = 20;
    private static final int MAX_WORD_COUNT = 100;
    private static final Random RANDOM = new Random();

    @Autowired
    private TestResultRepository testResultRepository;

    @Value("${ml.recommender.url:}")
    private String mlRecommenderUrl;

    private List<String> vocabularyCache;

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

    public StartTestResponse startTest(StartTestRequest request, User user) {
        int totalWordCount = bounded(
                Optional.ofNullable(request).map(StartTestRequest::totalWordCount).orElse(DEFAULT_TOTAL_WORD_COUNT),
                1,
                MAX_WORD_COUNT
        );
        int relevantWordCount = bounded(
                Optional.ofNullable(request).map(StartTestRequest::relevantWordCount).orElse(DEFAULT_RELEVANT_WORD_COUNT),
                0,
                totalWordCount
        );
        int lastN = bounded(
                Optional.ofNullable(request).map(StartTestRequest::lastN).orElse(DEFAULT_LAST_N),
                1,
                100
        );

        relevantWordCount = Math.max(totalWordCount, relevantWordCount);

        List<TestResult> recentResults = testResultRepository.findRecentByUser(
                user,
                PageRequest.of(0, lastN)
        );
        Collections.reverse(recentResults);

        List<String> relevantWords = recommendWords(recentResults, lastN, relevantWordCount)
                .stream()
                .limit(relevantWordCount)
                .toList();

        if (relevantWords.size() < relevantWordCount) {
            relevantWords = fillRelevantWordsFromHistory(relevantWords, recentResults, relevantWordCount);
        }

        List<String> fillerWords = randomVocabularyWords(totalWordCount - relevantWords.size(), relevantWords);
        List<String> testWords = new ArrayList<>();
        testWords.addAll(relevantWords);
        testWords.addAll(fillerWords);
        Collections.shuffle(testWords, RANDOM);

        return new StartTestResponse(
                String.join(" ", testWords),
                relevantWords,
                fillerWords
        );
    }

    private List<String> recommendWords(List<TestResult> recentResults, int lastN, int topK) {
        if (recentResults.isEmpty() || mlRecommenderUrl == null || mlRecommenderUrl.isBlank()) {
            return List.of();
        }

        List<List<Object>> data = new ArrayList<>();
        for (TestResult result : recentResults) {
            data.add(List.of(result.getTarget(), result.getTyped(), lastN, topK));
        }
        Map<String, Object> payload = Map.of(
                "dataframe_split",
                Map.of(
                        "columns", List.of("target", "typed", "last_n", "top_k"),
                        "data", data
                )
        );

        try {
            JsonNode response = RestClient.create()
                    .post()
                    .uri(mlRecommenderUrl)
                    .body(payload)
                    .retrieve()
                    .body(JsonNode.class);
            return parseMlRecommendations(response).stream()
                    .sorted(Comparator.comparingDouble(MlRecommendation::frequency).reversed())
                    .map(MlRecommendation::word)
                    .filter(word -> word != null && !word.isBlank())
                    .distinct()
                    .limit(topK)
                    .toList();
        } catch (RestClientException exception) {
            return List.of();
        }
    }

    private List<MlRecommendation> parseMlRecommendations(JsonNode response) {
        if (response == null) {
            return List.of();
        }

        JsonNode predictions = response.has("predictions") ? response.get("predictions") : response;
        if (!predictions.isArray()) {
            return List.of();
        }

        List<MlRecommendation> recommendations = new ArrayList<>();
        for (JsonNode node : predictions) {
            recommendations.add(new MlRecommendation(
                    node.path("word").asText(),
                    node.path("score").asDouble(0.0),
                    node.path("frequency").asDouble(0.0),
                    node.path("matched_trigrams").asText("")
            ));
        }
        return recommendations;
    }

    private List<String> fillRelevantWordsFromHistory(
            List<String> existingWords,
            List<TestResult> recentResults,
            int relevantWordCount
    ) {
        Map<String, Integer> counts = new LinkedHashMap<>();
        for (String word : existingWords) {
            counts.put(word, Integer.MAX_VALUE);
        }
        for (TestResult result : recentResults) {
            for (String word : missedWords(result.getTarget(), result.getTyped())) {
                counts.merge(word, 1, Integer::sum);
            }
        }
        List<String> words = counts.entrySet()
                .stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .map(Map.Entry::getKey)
                .filter(word -> word.length() >= 3)
                .distinct()
                .limit(relevantWordCount)
                .collect(Collectors.toCollection(ArrayList::new));

        if (words.size() < relevantWordCount) {
            words.addAll(randomVocabularyWords(relevantWordCount - words.size(), words));
        }
        return words.stream().limit(relevantWordCount).toList();
    }

    private List<String> missedWords(String target, String typed) {
        List<String> targetWords = normalizedWords(target);
        List<String> typedWords = normalizedWords(typed);
        List<String> missed = new ArrayList<>();
        for (String targetWord : targetWords) {
            if (!typedWords.contains(targetWord)) {
                missed.add(targetWord);
            }
        }
        return missed;
    }

    private List<String> normalizedWords(String text) {
        return WORD_PATTERN.matcher(text.toLowerCase(Locale.ROOT))
                .results()
                .map(match -> match.group())
                .filter(word -> word.length() >= 3)
                .toList();
    }

    private List<String> randomVocabularyWords(int count, List<String> excludedWords) {
        if (count <= 0) {
            return List.of();
        }

        List<String> vocabulary = new ArrayList<>(loadVocabulary());
        vocabulary.removeAll(excludedWords);
        Collections.shuffle(vocabulary, RANDOM);
        return vocabulary.stream().limit(count).toList();
    }

    private List<String> loadVocabulary() {
        if (vocabularyCache != null) {
            return vocabularyCache;
        }

        ClassPathResource resource = new ClassPathResource("static/20k");
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(resource.getInputStream(), StandardCharsets.UTF_8))) {
            vocabularyCache = reader.lines()
                    .map(line -> line.trim().toLowerCase(Locale.ROOT))
                    .filter(word -> word.matches("[a-z]{3,}"))
                    .toList();
            return vocabularyCache;
        } catch (IOException exception) {
            throw new IllegalStateException("Could not load static/20k vocabulary", exception);
        }
    }

    private int bounded(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }
}
