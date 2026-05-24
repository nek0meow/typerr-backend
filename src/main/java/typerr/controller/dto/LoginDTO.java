package typerr.controller.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class LoginDTO {

    @NotBlank(message = "Email не должен быть пустым")
    private String email;

    @Size(max = 255, message = "Длина должна быть не больее 255 символов")
    @NotBlank(message = "пароль не должен быть пустым")
    private String password;

    private boolean rememberMe;
}
