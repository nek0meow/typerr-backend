package typerr.controller;

import io.jsonwebtoken.Jwt;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import typerr.controller.data_forms.LoginForm;
import typerr.controller.data_forms.RegisterForm;
import typerr.model.User;
import typerr.repository.UserRepository;
import typerr.service.JwtService;
import typerr.service.UserService;

import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private UserService userService;
    @Autowired
    private JwtService jwtService;
    @Autowired
    private UserRepository userRepository;

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody RegisterForm data) {
        userService.registerUser(data.getUsername(), data.getEmail(), data.getPassword());
        return ResponseEntity.ok(Map.of("message", "Register success"));
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginForm data) {
        User user = userService.loginUser(data.getEmail(), data.getPassword());
        String token = jwtService.generateToken(user, data.isRememberMe());

        ResponseCookie cookie = ResponseCookie.from("jwt", token)
                .httpOnly(true)
                .secure(false)                // true in prod (HTTPS)
                .path("/")
                .maxAge(data.isRememberMe() ? 7 * 24 * 60 * 60 : 3600)
                .sameSite("Strict")
                .build();

        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, cookie.toString())
                .body(Map.of(
                        "message", "Login success",
                        "token", token
                ));
    }

    @GetMapping("/me")
    public ResponseEntity<?> getCurrentUser(
            @CookieValue(value = "jwt", required = false) String token) {

        if (token == null || !jwtService.validateToken(token)) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        Long userId = jwtService.extractUserId(token);
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.UNAUTHORIZED, "User not found"));

        return ResponseEntity.ok(Map.of(
                "username", user.getUsername(),
                "email", user.getEmail()
        ));
    }

}

