import { Container, Box, Typography, TextField, Button, MenuItem } from "@mui/material";

function Contact() {
    return (
        <Container maxWidth="sm">
            <Box sx={{ mt: 4 }}>
                <Typography variant="h4" gutterBottom>
                    Kontakt
                </Typography>

                <Typography variant="body1" sx={{ mb: 3 }}>
                    V prípade akýchkoľvek otázok alebo návrhov na zlepšenie ma môžete kontaktovať
                    prostredníctvom formulára uvedeného nižšie alebo e-mailom na adresu svitkovaandrea0@gmail.com.
                </Typography>

                <Box component="form" noValidate autoComplete="off">
                    <TextField
                        fullWidth
                        label="Meno (voliteľné)"
                        variant="outlined"
                        margin="normal"
                    />

                    <TextField
                        fullWidth
                        label="E-mail"
                        type="email"
                        variant="outlined"
                        margin="normal"
                        required
                    />

                    <TextField
                        fullWidth
                        select
                        label="Typ správy"
                        margin="normal"
                        defaultValue=""
                        required
                    >
                        <MenuItem value="bug">Chyba v aplikácii</MenuItem>
                        <MenuItem value="feature">Návrh na zlepšenie</MenuItem>
                        <MenuItem value="feedback">Všeobecná spätná väzba</MenuItem>
                    </TextField>

                    <TextField
                        fullWidth
                        label="Správa"
                        multiline
                        margin="normal"
                        required
                    />

                    <Box sx={{ mt: 3, textAlign: "right" }}>
                        <Button
                            variant="contained"
                            color="primary"
                        >
                            Odoslať
                        </Button>
                    </Box>
                </Box>
            </Box>
        </Container>
    );
}

export default Contact;
