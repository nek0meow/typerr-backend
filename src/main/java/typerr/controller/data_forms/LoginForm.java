package typerr.controller.data_forms;

import lombok.Data;

@Data
public class LoginForm {
    private String email;
    private String password;
    private boolean isRememberMe;
}
