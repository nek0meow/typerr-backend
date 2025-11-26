package typerr.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import typerr.controller.data_forms.CustomUserDetails;
import typerr.controller.data_forms.TestDataRequest;
import typerr.controller.data_forms.TestResultSimpleData;
import typerr.model.TestResult;
import typerr.service.ProfileService;
import typerr.service.TestService;

import java.util.List;

@RestController
@RequestMapping("/api/profile_stats")
public class ProfileController {

    @Autowired
    private ProfileService profileService;

    @GetMapping
    public ResponseEntity<?> getTestData(
            @AuthenticationPrincipal CustomUserDetails cud
    ) {
        if (cud == null || cud.getUser() == null) {
            System.out.println("cud is NULL!");
            return ResponseEntity.status(401).build();
        }

        List<TestResultSimpleData> results = profileService.getUserTestData(cud.getUser().getId());
        return ResponseEntity.ok(results);
    }

}
