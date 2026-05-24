package typerr.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import typerr.controller.dto.TestDataRequest;
import typerr.model.User;
import typerr.service.TestService;

@RestController
@RequestMapping("/api/test")
public class TestController {

    @Autowired
    private TestService testService;

    @PostMapping
    public ResponseEntity<?> saveTestData(
            @AuthenticationPrincipal User user,
            @RequestBody TestDataRequest data
    ) {
        testService.processTestResult(data, user);
        return ResponseEntity.ok().build();
    }
}
