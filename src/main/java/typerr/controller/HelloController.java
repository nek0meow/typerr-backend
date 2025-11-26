package typerr.controller;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "http://localhost:3000") // Allow Next.js frontend

public class HelloController {

    @GetMapping("/hello")
    public String hello() {
        return "<p style>Hello from Spring Boot!";
    }
}