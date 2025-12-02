import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.net.URI;

public class Main {

    public static void mostrarAviso() {
        JFrame frame = new JFrame();
        frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        frame.setSize(450, 160);
        frame.setLocationRelativeTo(null);
        frame.setLayout(new BorderLayout());
        frame.setTitle("Aviso MATH UP");

        JPanel painel = new JPanel();
        painel.setLayout(new BoxLayout(painel, BoxLayout.Y_AXIS));
        painel.setBorder(BorderFactory.createEmptyBorder(15, 15, 15, 15));

        JLabel texto = new JLabel("<html>Contate-nos para tornar sua experiência <b>MATH UP</b> ainda melhor:<br>"
                + "<a href='mailto:mathupajuda@gmail.com'>mathupajuda@gmail.com</a></html>");

        texto.setCursor(new Cursor(Cursor.HAND_CURSOR));

        texto.addMouseListener(new MouseAdapter() {
            @Override
            public void mouseClicked(MouseEvent e) {
                try {
                    Desktop.getDesktop().mail(new URI("mailto:mathupajuda@gmail.com"));
                } catch (Exception ex) {
                    ex.printStackTrace();
                }
            }
        });

        JButton fechar = new JButton("Fechar");
        fechar.addActionListener(e -> frame.dispose());

        painel.add(texto);
        painel.add(Box.createVerticalStrut(15));
        painel.add(fechar);

        frame.add(painel, BorderLayout.CENTER);
        frame.setVisible(true);
    }

    public static void main(String[] args) {
        mostrarAviso();
    }
}