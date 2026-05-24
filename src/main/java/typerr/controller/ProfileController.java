package typerr.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import typerr.controller.dto.TestResultSimpleData;
import typerr.model.User;
import typerr.service.ProfileService;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/profile_stats")
public class ProfileController {

    @Autowired
    private ProfileService profileService;

    @GetMapping
    public ResponseEntity<?> getTestData(
            Authentication authentication
    ) {
        User user = (User) authentication.getPrincipal();
        if (user == null) {
            System.out.println("user is NULL!");
            return ResponseEntity
                    .status(401)
                    .header(Map.of("message", "user is NULL").toString())
                    .build();
        }

        List<TestResultSimpleData> results = profileService.getUserTestData(user.getId());
        return ResponseEntity.ok(results);
    }

}
