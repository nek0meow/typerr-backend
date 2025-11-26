package typerr.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import typerr.controller.data_forms.CustomUserDetails;
import typerr.controller.data_forms.TestDataRequest;
import typerr.model.User;
import typerr.service.TestService;

@RestController
@RequestMapping("/api/test")
public class TestController {

    @Autowired
    private TestService testService;

    @PostMapping
    public ResponseEntity<?> saveTestData(
            @AuthenticationPrincipal CustomUserDetails cud,
            @RequestBody TestDataRequest data
    ) {
        testService.processTestResult(data, cud.getUser());
        return ResponseEntity.ok().build();
    }
}
