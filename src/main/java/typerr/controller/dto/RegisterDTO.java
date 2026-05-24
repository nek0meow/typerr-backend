package typerr.controller.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
public class RegisterDTO {

    @NotBlank(message = "Имя пользователя не должно быть пустым")
    private String username;

    @NotBlank(message = "Email не должен быть пустым")
    private String email;

    @Size(max = 255, message = "Длина должна быть не более 255 символов")
    @NotBlank(message = "пароль не должен быть пустым")
    private String password;
}

