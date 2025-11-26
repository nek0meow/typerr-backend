package typerr.service;

import java.util.List;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import typerr.controller.data_forms.CustomUserDetails;
import typerr.repository.UserRepository;

import java.io.IOException;

@Component
public class JwtAuthFilter extends OncePerRequestFilter {

    @Autowired
    private JwtService jwtService;
    @Autowired
    private UserRepository userRepository;


    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {

        Cookie[] cookies = request.getCookies();
        if (cookies == null) {
            filterChain.doFilter(request, response);
            return;
        }

        String token = null;
        for (Cookie c : cookies) {
            if ("jwt".equals(c.getName())) {
                token = c.getValue();
                break;
            }
        }

        if (token != null && jwtService.validateToken(token)) {
            Long userId = jwtService.extractUserId(token);
            userRepository.findById(userId).ifPresent(user -> {
                CustomUserDetails cud = new CustomUserDetails(user);
                UsernamePasswordAuthenticationToken auth =
                        new UsernamePasswordAuthenticationToken(
                                cud,
                                null,
                                cud.getAuthorities()
                        );
                SecurityContextHolder.getContext().setAuthentication(auth);
            });
        }



        filterChain.doFilter(request, response);
    }
}