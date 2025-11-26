package typerr.controller.data_forms;

import lombok.Data;

@Data
public class LoginRequest {
    private String email;
    private String password;
}
