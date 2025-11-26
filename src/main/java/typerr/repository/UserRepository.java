package typerr.repository;

import typerr.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface UserRepository extends JpaRepository<User, Long> {
    public User getUserById(Long id);
    public List<User> getUsers();
}
