package com.changmeen.grauduation_project_app;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.core.content.FileProvider;

import android.Manifest;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.media.MediaScannerConnection;
import android.os.Environment;
import android.os.Handler;
import android.os.ParcelFileDescriptor;
import android.provider.MediaStore;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.AsyncTask;
import android.os.Build;
import android.os.Bundle;
import android.provider.DocumentsContract;
import android.provider.MediaStore;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.BufferedWriter;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.Serializable;
import java.net.Socket;
import java.net.UnknownHostException;
import java.nio.ByteBuffer;
import java.lang.System;

public class MainActivity extends AppCompatActivity {
    private Handler mHandler;
    private static final int REQUEST_CODE = 0;
    private static final int SELECT_PICTURE = 1;
    private static final int TAKE_PICTURE = 2;
    private final int MY_PERMISSIONS_REQUEST_CAMERA=1001;
    private String TAG = " ";
    ImageButton send_button;
    ImageButton send_button2;
    ImageView image_view;
    private Bitmap img;
    private static String SERVER_IP = "192.168.47.1";
    private static String CONNECT_MSG = "connect";
    private static String STOP_MSG = "stop";
    private File file;
    private String currentPhotoPath;
    private Uri photoUri;
    private Socket socket;

    private static int BUF_SIZE = 100;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        send_button = findViewById(R.id.send_button);
        send_button2 = findViewById(R.id.send_button2);
        image_view = findViewById(R.id.imageView);

        int permssionCheck = ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA);

        if (permssionCheck!= PackageManager.PERMISSION_GRANTED) {
            Toast.makeText(this,"권한 승인이 필요합니다",Toast.LENGTH_LONG).show();
            if (ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.CAMERA)) {
                Toast.makeText(this,"000부분 사용을 위해 카메라 권한이 필요합니다.",Toast.LENGTH_LONG).show();
            }
            else {
                ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.CAMERA}, MY_PERMISSIONS_REQUEST_CAMERA);
                Toast.makeText(this,"000부분 사용을 위해 카메라 권한이 필요합니다.",Toast.LENGTH_LONG).show();
            }
        }


        send_button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                openGallery();
            }
        });

        send_button2.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                takePhoto();
            }
        });
    }

    // 권한 요청
    @Override
    public void onRequestPermissionsResult(int requestCode, String permissions[], int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        switch (requestCode) {
            case MY_PERMISSIONS_REQUEST_CAMERA: { // If request is cancelled, the result arrays are empty
                if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    Toast.makeText(this, "승인이 허가되어 있습니다.", Toast.LENGTH_LONG).show();
                } else {
                    Toast.makeText(this, "아직 승인받지 않았습니다.", Toast.LENGTH_LONG).show();
                }
                return;
            }
        }
    }

    private void openGallery(){
        Intent intent = new Intent();
        intent.setType("image/*");
        intent.setAction(Intent.ACTION_GET_CONTENT);
        startActivityForResult(intent, SELECT_PICTURE);
    }

    private void takePhoto() {
        Intent intent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);

        try {
            file = createImageFile();
        } catch (IOException e) {
            Toast.makeText(this, "이미지 처리 오류! 다시 시도해주세요.", Toast.LENGTH_SHORT).show();
            finish();
            e.printStackTrace();
        }
        if (file != null) {
            photoUri = FileProvider.getUriForFile(this, getPackageName(), file);
            intent.putExtra(MediaStore.EXTRA_OUTPUT, photoUri);
            startActivityForResult(intent, TAKE_PICTURE);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        switch (requestCode){
            case SELECT_PICTURE:
                if (resultCode == RESULT_OK) {
                    InputStream in = null;
                    try {
                        in = getContentResolver().openInputStream(data.getData());
                        img = BitmapFactory.decodeStream(in);
                        in.close();
                        mHandler = new Handler();
                        checkUpdate.start();

                    } catch (FileNotFoundException e) {
                        e.printStackTrace();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                } else if (resultCode == RESULT_CANCELED) {

                    Toast.makeText(this, "사진 선택 취소", Toast.LENGTH_LONG).show();
                } break;

            case TAKE_PICTURE:
                if (resultCode == RESULT_OK) {
                    InputStream in = null;
                    try {
                        in = getContentResolver().openInputStream(photoUri);
                        img = BitmapFactory.decodeStream(in);
                        in.close();
                        checkUpdate.start();

                    } catch (FileNotFoundException e) {
                        e.printStackTrace();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                    break;
                }
        }
    }

    private Thread checkUpdate = new Thread() {
        DataInputStream dis;
        DataOutputStream dos;
        ByteArrayOutputStream bos;
        BufferedOutputStream bos2;

        public void run() {
            try {
                socket = new Socket(SERVER_IP, 8080);

                try {
                    dis = new DataInputStream(socket.getInputStream());
                    dos = new DataOutputStream(socket.getOutputStream());
                    bos = new ByteArrayOutputStream();
                } catch (IOException e) {
                    e.printStackTrace();
                }

                try {
                    img.compress(Bitmap.CompressFormat.JPEG, 100, bos);
                    bos.flush();
                    byte[] array = bos.toByteArray();
                    dos.writeInt(array.length);
                    dos.write(array);
                    dos.flush();

                    dis = new DataInputStream(socket.getInputStream());
                    File f = new File(getFilesDir(), "complete_picture.jpg");
                    FileOutputStream output = new FileOutputStream(f);
                    bos2 = new BufferedOutputStream(output);

                    int readdata = 0;
                    byte[] buf = new byte[1024];

                    while((readdata = dis.read(buf)) != -1) {
                        bos2.write(buf, 0, readdata);
                        bos2.flush();
                    }

                    mHandler.post(showUpdate);

                } catch (IOException e) {
                    e.printStackTrace();
                }finally {
                    dos.close();
                    dos.close();
                    socket.close();
                }

            } catch (UnknownHostException e) {
                e.printStackTrace();
            } catch (IOException e){
                e.printStackTrace();
            }
        }
    };

    private Runnable showUpdate = new Runnable() {
        @Override
        public void run() {
            String imgpath = getFilesDir() + "/" + "complete_picture.jpg";
            Bitmap bm = BitmapFactory.decodeFile(imgpath);
            image_view.setImageBitmap(bm);
        }
    };

    private File createImageFile() throws IOException {

        File storageDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        File image = File.createTempFile(
                "dog",  /* prefix */
                ".jpg",         /* suffix */
                storageDir      /* directory */
        );
        currentPhotoPath = image.getAbsolutePath();
        return image;
    }
}